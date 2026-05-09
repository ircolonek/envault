# envault

> Secure environment variable manager that encrypts `.env` files and syncs them across team members via a shared backend.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) for global CLI use:

```bash
pipx install envault
```

---

## Usage

**Initialize envault in your project:**

```bash
envault init
```

**Push your `.env` file to the shared backend:**

```bash
envault push --env .env
```

**Pull the latest secrets to your local machine:**

```bash
envault pull --env .env
```

**Encrypt a `.env` file manually:**

```bash
envault encrypt .env --out .env.vault
```

All secrets are AES-256 encrypted before leaving your machine. Only team members with the shared key can decrypt them.

---

## How It Works

1. `envault` encrypts your `.env` file using a project-specific key.
2. The encrypted vault is pushed to a configured backend (S3, a REST API, or local storage).
3. Team members run `envault pull` to fetch and decrypt the latest secrets locally.

---

## Configuration

Create an `envault.toml` in your project root:

```toml
[backend]
type = "s3"
bucket = "my-team-secrets"
region = "us-east-1"
```

---

## License

[MIT](LICENSE) © 2024 envault contributors