# DRM Protection

DRM Protection is a multi‑component system designed to securely manage digital rights for media content. It provides tools for encryption, license issuance, and client‑side decryption, organized into distinct modules for the server, client, admin interface, and infrastructure.

## Key Features

* **Asymmetric Cryptography**: Utilizes RSA public/private key pairs for secure content encryption and license validation.
* **Modular Architecture**: Clear separation into `admin/`, `server/`, `client/`, and `infra/` directories to streamline development and maintenance.
* **Containerized Deployment**: Docker and Docker Compose configurations ensure consistent, reproducible environments across teams.
* **CI/CD Ready**: GitHub Actions workflows automate testing, building, and deployment of each component.

## Architecture Overview

```text
+------------+      +-------------+      +----------+
|  Admin UI  |----->|  License    |----->|  Client  |
| (admin/)   |      |  Server     |      | (client/)
+------------+      | (server/)   |      +----------+
                    +-------------+
                          |
                          v
                    +-------------+
                    | Encrypted   |
                    | Media Store |
                    +-------------+
```

* **Admin UI** (`admin/`): React‑based dashboard for managing media assets, user roles, and issuing licenses.
* **License Server** (`server/`): FastAPI service handling license generation, validation, and key management.
* **Client** (`client/`): Python CLI/SDK that requests licenses, decrypts protected content, and streams or saves media.
* **Infrastructure** (`infra/`): Docker Compose, NGINX, and environment configurations for seamless deployment.

## Getting Started

### Prerequisites

* [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) (v1.29+)
* Python 3.9+ with `pip`
* Node.js & npm (for Admin UI)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/CreatorT/drm-protection.git
   cd drm-protection
   ```

2. **Generate RSA key pair**

   ```bash
   openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:2048
   openssl rsa -pubout -in private.pem -out public.pem
   ```

3. **Start all services with Docker Compose**

   ```bash
   docker-compose up --build -d
   ```

4. **Verify services**

   * Admin UI: `http://localhost:3000`
   * License Server API: `http://localhost:8000`

### Local Development

**Server**

```bash
cd server\
// install dependencies
pip install -r requirements.txt
# run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Client**

```bash
cd client\
// install dependencies
pip install -r requirements.txt
# request a license and decrypt content\python client.py --request-license <content_id>
```

**Admin UI**

```bash
cd admin
npm install
eplynpm run dev
```

## Configuration

Each component reads environment variables from a `.env` file in its root:

* `PRIVATE_KEY_PATH` / `PUBLIC_KEY_PATH`: Paths to RSA keys.
* `DATABASE_URL`: Connection string for the License Server.
* `NGINX_CONF`: Path to NGINX configuration in `infra/`.

Copy and customize the provided `.env.example` files in each folder.

## Directory Structure

```text
├── admin/         # React dashboard for administrators
├── client/        # Python CLI/SDK for license requests & decryption
├── server/        # FastAPI license server
├── infra/         # Docker Compose, NGINX, and deployment configs
├── public.pem     # RSA public key (ignore in commits)
├── private.pem    # RSA private key (ignore in commits)
└── docker-compose.yml
```

## Testing

* **Server tests**:

  ```bash
  cd server && pytest
  ```
* **Client tests**:

  ```bash
  cd client && pytest
  ```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a branch: `git checkout -b feature/YourFeature`.
3. Commit your changes: `git commit -m "Add your feature"`.
4. Push to your fork: `git push origin feature/YourFeature`.
5. Open a Pull Request against `main`.

## License

This project is licensed under the [MIT License](LICENSE).
