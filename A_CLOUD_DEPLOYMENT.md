# Cloud Deployment Guide: Templo Atelier (v8.0)

This guide provides instructions for deploying your Studio OS to the cloud and making it accessible via `temploatelier.com`.

## 1. Local Verification (Docker)
Before pushing to the cloud, verify the container works locally:
```bash
docker-compose up --build
```
Once running, visit `http://localhost:8000`. You should see the premium Studio OS dashboard.

## 2. Cloud Providers (Recommendations)
The system is standard Docker, making it compatible with:
- **Render.com** (Simplest): Create a "Web Service", connect your repo, and it will auto-detect the Dockerfile.
- **Railway.app**: Excellent for FastAPI/PostgreSQL/Docker stacks.
- **DigitalOcean App Platform**: Robust for scaling.

## 3. Positioning the Domain (`temploatelier.com`)
1.  **Configure DNS**: In your domain registrar (GoDaddy, Namecheap, etc.), create a **CNAME** or **A record** pointing to your cloud provider's host.
2.  **SSL/TLS**: Most modern providers (Render, Railway) provide automatic SSL. Ensure "Enforce HTTPS" is active.
3.  **Environment Variables**:
    - `GEMINI_API_KEY`: Your key from Google AI Studio.
    - `GOOGLE_APPLICATION_CREDENTIALS_JSON`: The raw content of your service account key.
    - `DATABASE_URL`: (Optional) Point to a managed PostgreSQL instance for 100% persistence.

## 4. Scaling the Studio
- **10 Projects**: Standard instance is fine.
- **50+ Projects**: Consider upgrading to 2GB RAM and a separate PostgreSQL instance for the state cache.

---
*Templo Atelier: 2026-Native Creative Intelligence*
