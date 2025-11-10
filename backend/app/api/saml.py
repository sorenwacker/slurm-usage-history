"""SAML SSO endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

from ..core.saml_auth import (
    create_session_token,
    get_current_user_saml,
    init_saml_auth,
    is_saml_enabled,
)

router = APIRouter()


@router.get("/login")
async def saml_login(request: Request, redirect_to: Optional[str] = None):
    """Initiate SAML login.

    Args:
        request: FastAPI request object
        redirect_to: Optional URL to redirect to after login

    Returns:
        Redirect to IdP login page
    """
    if not is_saml_enabled():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="SAML authentication is not enabled",
        )

    auth = init_saml_auth(request)

    # Store redirect URL in session if provided
    # For simplicity, we'll pass it as RelayState
    relay_state = redirect_to or "/"

    sso_url = auth.login(return_to=relay_state)
    return RedirectResponse(url=sso_url, status_code=status.HTTP_302_FOUND)


@router.post("/acs")
async def saml_acs(request: Request):
    """Assertion Consumer Service - handles SAML response from IdP.

    Args:
        request: FastAPI request object with SAML response

    Returns:
        Redirect to application with session cookie
    """
    if not is_saml_enabled():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="SAML authentication is not enabled",
        )

    # Get POST data
    form_data = await request.form()

    # Map new-style URLs to old-style for SAML validation
    # This allows nginx rewrites from /?acs to /saml/acs to work
    script_name = request.url.path
    if script_name == "/saml/acs":
        script_name = "/"
        query_string = "acs"
    else:
        query_string = ""

    # Prepare request data for python3-saml
    request_data = {
        "https": "on" if request.url.scheme == "https" else "off",
        "http_host": request.url.hostname,
        "server_port": request.url.port or (443 if request.url.scheme == "https" else 80),
        "script_name": script_name,
        "query_string": query_string,
        "get_data": dict(request.query_params),
        "post_data": dict(form_data),
    }

    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from ..core.saml_auth import load_saml_settings

    saml_settings = load_saml_settings()
    auth = OneLogin_Saml2_Auth(request_data, saml_settings)

    auth.process_response()
    errors = auth.get_errors()

    if errors:
        error_reason = auth.get_last_error_reason()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SAML authentication failed: {error_reason}",
        )

    if not auth.is_authenticated():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SAML authentication failed",
        )

    # Get user attributes
    attributes = auth.get_attributes()
    nameid = auth.get_nameid()
    session_index = auth.get_session_index()

    # Create user data for session
    user_data = {
        "username": nameid,
        "attributes": attributes,
        "session_index": session_index,
    }

    # Create JWT session token
    session_token = create_session_token(user_data)

    # Get relay state (redirect URL)
    relay_state = request_data.get("post_data", {}).get("RelayState", "/")

    # Create response with cookie
    response = RedirectResponse(url=relay_state, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="session_token",
        value=session_token,
        path="/",
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        max_age=86400,  # 24 hours
    )

    return response


@router.get("/metadata")
async def saml_metadata(request: Request):
    """Return SAML SP metadata XML.

    Args:
        request: FastAPI request object

    Returns:
        XML metadata document
    """
    if not is_saml_enabled():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="SAML authentication is not enabled",
        )

    auth = init_saml_auth(request)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if errors:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid SAML metadata: {', '.join(errors)}",
        )

    return Response(content=metadata, media_type="application/xml")


@router.get("/sls")
@router.post("/sls")
async def saml_sls(request: Request):
    """Single Logout Service - handles logout requests.

    Args:
        request: FastAPI request object

    Returns:
        Redirect response
    """
    if not is_saml_enabled():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="SAML authentication is not enabled",
        )

    auth = init_saml_auth(request)

    # For POST requests, get form data
    if request.method == "POST":
        form_data = await request.form()

        # Map new-style URLs to old-style for SAML validation
        script_name = request.url.path
        if script_name == "/saml/sls":
            script_name = "/"
            query_string = "sls"
        else:
            query_string = ""

        request_data = {
            "https": "on" if request.url.scheme == "https" else "off",
            "http_host": request.url.hostname,
            "server_port": request.url.port or (443 if request.url.scheme == "https" else 80),
            "script_name": script_name,
            "query_string": query_string,
            "get_data": dict(request.query_params),
            "post_data": dict(form_data),
        }
        from onelogin.saml2.auth import OneLogin_Saml2_Auth
        from ..core.saml_auth import load_saml_settings

        saml_settings = load_saml_settings()
        auth = OneLogin_Saml2_Auth(request_data, saml_settings)

    # Process logout
    url = auth.process_slo(delete_session_cb=lambda: None)
    errors = auth.get_errors()

    if errors:
        error_reason = auth.get_last_error_reason()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SAML logout failed: {error_reason}",
        )

    # Clear session cookie
    response = RedirectResponse(url=url or "/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="session_token", path="/")

    return response


@router.get("/logout")
async def saml_logout(request: Request):
    """Initiate SAML logout.

    Args:
        request: FastAPI request object

    Returns:
        Redirect to IdP logout
    """
    if not is_saml_enabled():
        # Just clear cookie and redirect
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.delete_cookie(key="session_token", path="/")
        return response

    auth = init_saml_auth(request)

    # Get session index from user's session
    # In a real implementation, you'd retrieve this from the user's session
    slo_url = auth.logout()

    response = RedirectResponse(url=slo_url, status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="session_token", path="/")

    return response


@router.get("/status")
async def saml_status(request: Request):
    """Check SAML authentication status.

    Returns:
        SAML configuration status
    """
    return {
        "enabled": is_saml_enabled(),
        "configured": is_saml_enabled(),
    }


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user_saml)):
    """Get current authenticated user information including role.

    Returns:
        User information with role (admin/user)
    """
    from ..core.config import get_settings

    settings = get_settings()

    # Extract email from SAML attributes
    email = None
    if "attributes" in current_user and current_user["attributes"]:
        # Try common SAML email attribute names
        email_attrs = current_user["attributes"].get("email") or \
                     current_user["attributes"].get("mail") or \
                     current_user["attributes"].get("emailAddress")
        if email_attrs and isinstance(email_attrs, list) and len(email_attrs) > 0:
            email = email_attrs[0]

    # Check if user is admin
    is_admin = False
    if email:
        is_admin = settings.is_admin_email(email)

    # If not found by email, check if username (netid) matches any admin email prefix
    # E.g., username "sdrwacker" matches "sdrwacker@tudelft.nl"
    if not is_admin and current_user.get("username"):
        username = current_user.get("username")
        # Check if username@tudelft.nl is in admin emails
        full_email = f"{username}@tudelft.nl"
        is_admin = settings.is_admin_email(full_email)
        # If we found a match, use the constructed email
        if is_admin and not email:
            email = full_email

    return {
        "username": current_user.get("username"),
        "email": email,
        "is_admin": is_admin,
        "attributes": current_user.get("attributes", {}),
    }
