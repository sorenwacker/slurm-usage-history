# A pytest example
# Run with: pytest


def test_example():
    # Check that we can import and call the main function
    from python_template.main import main

    main()
    assert True
