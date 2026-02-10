# ShareME. 🚀 
### Premium Encrypted P2P File Server — Built by Kunal

<div align="center">
  <img src="favicon.ico" width="128" height="128" />
  <p align="center">
    <strong>The fastest, most secure way to share files directly from your disk to the world.</strong>
    <br />
    <em>100% Open Source. No cloud storage. No size limits. Total Privacy.</em>
  </p>

  <p align="center">
    <a href="https://github.com/kunalsinghks/ShareMe/stargazers"><img src="https://img.shields.io/github/stars/kunalsinghks/ShareMe?style=for-the-badge&color=6366f1&logo=github" alt="Stars" /></a>
    <a href="https://github.com/kunalsinghks/ShareMe/releases"><img src="https://img.shields.io/github/downloads/kunalsinghks/ShareMe/total?style=for-the-badge&color=818cf8&logo=windows" alt="Downloads" /></a>
    <a href="https://github.com/kunalsinghks/ShareMe/blob/main/LICENSE"><img src="https://img.shields.io/github/license/kunalsinghks/ShareMe?style=for-the-badge&color=4f46e5" alt="License" /></a>
  </p>
</div>

---

## 📖 Deep Dive: How ShareME Works

ShareME is built on the principle of **Direct Sovereignty**. Unlike traditional file-sharing services (GoFile, WeTransfer) that store your files on their servers, ShareME creates a temporary, encrypted "bridge" directly to your local computer.

### 🏗️ Architecture
1. **Local Backend**: A high-performance **FastAPI** server running on your machine indexes the files you choose to share.
2. **The Bridge**: Using **Cloudflare Tunnels (Argo)**, we create a secure tunnel from your local port `8000` to an encrypted `trycloudflare.com` URL.
3. **No Config**: This technique bypasses **CGNAT**, firewalls, and router settings. You don't need to touch your router or deal with port forwarding.
4. **Security**: The data is encrypted in transit between the uploader and the downloader via Cloudflare's global edge network.

---

## 🛡️ Security & Privacy
- **E2EE (End-to-End Encryption)**: Data is encrypted via HTTPS using Cloudflare's Tier-1 security infrastructure.
- **Zero Retention**: Files stay on your disk. They are never cached or stored in any cloud bucket.
- **Vault Protection**: Enable an optional access password. The server uses local authentication to ensure only people with the key can see your files.

---

## 📥 Downloads (v1.2.0 Official Multi-Platform)

We offer professional installers and portable binaries for all major Operating Systems.

| Platform | Download | format |
| :--- | :--- | :--- |
| **Windows** | [**Download Installer (Setup)**](https://github.com/kunalsinghks/ShareMe/releases/download/v1.2.0/ShareMe_Windows_Installer_Package.zip) | `.zip` (contains .exe) |
| **Windows** | [**Download Portable**](https://github.com/kunalsinghks/ShareMe/releases/download/v1.2.0/ShareME_Windows_Portable.zip) | `.zip` |
| **macOS** | [**Download for Mac (Intel/M1/M2)**](https://github.com/kunalsinghks/ShareMe/releases/download/v1.2.0/ShareME_Mac_Portable.zip) | `.zip` |
| **Linux** | [**Download for Linux**](https://github.com/kunalsinghks/ShareMe/releases/download/v1.2.0/ShareME_Linux_Portable.tar.gz) | `.tar.gz` |

---

## 🛠️ Open Source Development

We welcome the community to audit, improve, and fork ShareME.

### Prerequisites
- Python 3.10+
- Node.js (for `npx cloudflared`)

### Local Setup
```bash
# 1. Clone the repository
git clone https://github.com/kunalsinghks/ShareMe.git
cd ShareMe

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the dashboard
python gui.py
```

### Packaging (Build your own labels)
```bash
# Build the core app
pyinstaller ShareME.spec

# Build the GUI Installer (Windows)
python -m PyInstaller --onefile --windowed --icon=favicon.ico --name ShareMe_Setup gui_installer.py
```

---

<div align="center">
  <h3>Made with ❤️ by Kunal</h3>
  <p><i>Building a more private and decentralised web.</i></p>
</div>
