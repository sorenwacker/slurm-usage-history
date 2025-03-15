# slurm-usage-history

`slurm-usage-history` is a Python package designed to analyze and visualize SLURM usage history. It provides tools to fetch, process, and display SLURM job data, helping users understand resource utilization and job performance over time.

## Features

- Fetch SLURM usage data from remote servers
- Process and analyze SLURM job data
- Visualize usage history with interactive dashboards
- Integrate with Flask for web-based visualization
- Support for SAML2 authentication

## Installation

To install the package, use the following command:

```sh
pip install slurm-usage-history
```

## Usage

### Fetching Data

To fetch SLURM usage data from a remote server, use the `getdata` command:

```sh
make getdata
```

### Running the Dashboard

To run the SLURM usage dashboard, use the `serve` command:

```sh
make serve
```

### Development Mode

To run the dashboard in development mode with debugging enabled, use the `devel` command:

```sh
make devel
```


## SAML2 Authentication

To set up SAML2 authentication, follow these steps:

### 1. Place your SAML configuration files in the `saml` folder.

```
saml/
├── advanced_settings.json
├── certs
│   ├── idp-cert.pem
│   ├── idp_metadata.xml
│   ├── README
│   ├── sp_cert_one_line.txt
│   ├── sp.crt
│   └── sp.key
└── settings.json
```

#### saml/advanced_settings.json

```bash
{
    "security": {
        "nameIdEncrypted": false,
        "authnRequestsSigned": false,
        "logoutRequestSigned": false,
        "logoutResponseSigned": false,
        "signMetadata": false,
        "wantMessagesSigned": false,
        "wantAssertionsSigned": false,
        "wantNameId" : true,
        "wantNameIdEncrypted": false,
        "wantAssertionsEncrypted": false,
        "allowSingleLabelDomains": false,
        "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
        "digestAlgorithm": "http://www.w3.org/2001/04/xmlenc#sha256",
        "rejectDeprecatedAlgorithm": true
    },
    "contactPerson": {
        "technical": {
            "givenName": "Your Name",
            "emailAddress": "example@email.com"
        },
        "support": {
            "givenName": "Your Name",
            "emailAddress": "example@email.com"
        }
    },
    "organization": {
        "en-US": {
            "name": "Slurm Dashboard",
            "displayname": "Slurm Dashboard",
            "url": "https://dashboard.daic.tudelft.nl"
        }
    }
}
```


### 2. Use the wsgi-saml.py

The `wsgi-saml.py` script wraps the dashboard with an authentication layer using SAML2.

Example command to run the application with SAML2:

```sh
gunicorn -w 1 -b 0.0.0.0:8080 wsgi-saml:app
```

### Environment Variables

The application uses a `.env` file to manage environment-specific settings. Create a `.env` file in the root directory of your project and add the necessary configuration variables. 
Here is an example of what the `.env` file should look like:

#### .env
```bash
SLURM_USAGE_HISTORY_DATA_PATH=/path/to/slurm-usage-history/data
FLASK_SECRET_KEY=...
```

## Contributing

We welcome contributions to the `slurm-usage-history` project. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) and [Contributing Guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the GNU General Public License v3.0. See the [`LICENSE`](LICENSE ) file for details.

## Contact

For any questions or feedback, please contact Sören Wacker at s.wacker@gmail.com.
