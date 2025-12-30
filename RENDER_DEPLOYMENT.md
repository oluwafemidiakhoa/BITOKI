# Deploy BITfisher to Render.com

## Quick Start

1. **Create a Render Account**
   - Go to https://render.com/
   - Sign up with your GitHub account

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `oluwafemidiakhoa/BITfisher`
   - Render will auto-detect the `render.yaml` configuration

3. **Configure Environment Variables**
   Render will create these automatically from `render.yaml`:
   - `FLASK_SECRET_KEY` (auto-generated)
   - `DATABASE_URL` (from PostgreSQL database)
   - `FLASK_ENV` = production
   
   **You need to add these manually:**
   - `PAYSTACK_SECRET_KEY` = your_paystack_key
   - `EXCHANGE_API_KEY` = your_binance_key
   - `EXCHANGE_API_SECRET` = your_binance_secret

4. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for initial deployment
   - Your app will be live at: `https://bitoki.onrender.com`

## Features Included

✅ Free PostgreSQL database (faster than SQLite)
✅ Automatic HTTPS/SSL certificate
✅ Auto-deploy on git push
✅ Health checks and auto-restart
✅ Build logs and monitoring

## Cost

- **Free Tier**: Perfect for testing
  - Spins down after 15 minutes of inactivity
  - Takes 30-60 seconds to wake up on first request
  
- **Paid Tier**: $7/month
  - Always online
  - No cold starts
  - Better performance

## After Deployment

1. Visit your app URL
2. Register a new account
3. Change admin password
4. Enable 2FA
5. Test all features

## Troubleshooting

If deployment fails, check:
1. Build logs in Render dashboard
2. Environment variables are set correctly
3. Database is connected
4. All dependencies in requirements.txt

## Support

For issues, check: https://render.com/docs
