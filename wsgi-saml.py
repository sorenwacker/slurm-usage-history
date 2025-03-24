import os
from flask import Flask, request, render_template, redirect, session, make_response
from urllib.parse import urlparse
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from slurm_usage_history.app.app import create_dash_app
from dotenv import load_dotenv

load_dotenv()

# Define the Args class to hold configuration
class Args:
    data_path = os.getenv("SLURM_USAGE_HISTORY_DATA_PATH", "slurmo")

args = Args()

# Initialize the Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
app.config["SAML_PATH"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "saml"
)

def init_saml_auth(req):
    # Fixed RET504 - Return directly without unnecessary assignment
    return OneLogin_Saml2_Auth(req, custom_base_path=app.config["SAML_PATH"])


def prepare_flask_request(request):
    url_data = urlparse(request.url)
    return {
        "https": "on" if request.scheme == "https" else "off",
        "http_host": request.host,
        "server_port": url_data.port,
        "script_name": request.path,
        "get_data": request.args.copy(),
        "post_data": request.form.copy(),
        "query_string": request.query_string,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    if "sso" in request.args:
        return redirect(auth.login())
    elif "sso2" in request.args:
        # Fixed UP031 - Use f-string instead of percent format
        return_to = f"{request.host_url}attrs/"
        return redirect(auth.login(return_to))
    elif "slo" in request.args:
        name_id = session.get("samlNameId")
        session_index = session.get("samlSessionIndex")
        name_id_format = session.get("samlNameIdFormat")
        name_id_nq = session.get("samlNameIdNameQualifier")
        name_id_spnq = session.get("samlNameIdSPNameQualifier")

        return redirect(
            auth.logout(
                name_id=name_id,
                session_index=session_index,
                nq=name_id_nq,
                name_id_format=name_id_format,
                spnq=name_id_spnq,
            )
        )
    elif "acs" in request.args:
        request_id = session.get("AuthNRequestID")
        auth.process_response(request_id=request_id)
        errors = auth.get_errors()
        not_auth_warn = not auth.is_authenticated()
        if len(errors) == 0:
            if "AuthNRequestID" in session:
                del session["AuthNRequestID"]
            session["samlUserdata"] = auth.get_attributes()
            session["samlNameIdFormat"] = auth.get_nameid_format()
            session["samlNameIdNameQualifier"] = auth.get_nameid_nq()
            session["samlNameIdSPNameQualifier"] = auth.get_nameid_spnq()
            session["samlSessionIndex"] = auth.get_session_index()
            self_url = OneLogin_Saml2_Utils.get_self_url(req)
            if "RelayState" in request.form and self_url != request.form["RelayState"]:
                return redirect(auth.redirect_to(request.form["RelayState"]))
        elif auth.get_settings().is_debug_active():
            error_reason = auth.get_last_error_reason()
    elif "sls" in request.args:
        request_id = session.get("LogoutRequestID")
        # Fixed E731 - Use def instead of lambda
        def dscb():
            session.clear()
        url = auth.process_slo(request_id=request_id, delete_session_cb=dscb)
        errors = auth.get_errors()
        if len(errors) == 0:
            if url is not None:
                return redirect(url)
            else:
                success_slo = True
        elif auth.get_settings().is_debug_active():
            error_reason = auth.get_last_error_reason()

    if "samlUserdata" in session:
        paint_logout = True
        if len(session["samlUserdata"]) > 0:
            # Fixed F841 - Remove unused variable or use it
            # We'll remove the assignment since it's commented out in the template rendering
            pass
        # Fixed UP031 - Use f-string instead of percent format
        return_to = f"{request.host_url}dashboard/"
        return redirect(auth.login(return_to))

    return render_template(
        "index.html",
        errors=errors,
        error_reason=error_reason,
        not_auth_warn=not_auth_warn,
        success_slo=success_slo,
        # attributes=attributes,
        paint_logout=paint_logout,
    )


@app.route("/attrs/")
def attrs():
    paint_logout = False
    attributes = False

    if "samlUserdata" in session:
        paint_logout = True
        if len(session["samlUserdata"]) > 0:
            attributes = session["samlUserdata"].items()

    return render_template(
        "attrs.html", paint_logout=paint_logout, attributes=attributes
    )


@app.route("/logout/")
def logout():
    return redirect("/?slo")


@app.route("/metadata/")
def metadata():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = make_response(metadata, 200)
        resp.headers["Content-Type"] = "text/xml"
    else:
        resp = make_response(", ".join(errors), 500)
    return resp


# Initialize the Dash app on the '/dashboard/' route
dash_app = create_dash_app(args, server=app, url_base_pathname="/dashboard/")


# Middleware to check authentication before accessing the Dash app
@app.before_request
def check_authentication():
    # Check if the request is for the Dash app
    if request.path.startswith("/dashboard/") and "samlUserdata" not in session:
        return redirect("/?sso")  # Redirect to login if not authenticated
    # Fixed RET503 - Add explicit return
    return None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)