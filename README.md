# Receipt_wala - AI-Powered Receipt Processing API

A FastAPI-based service that uses Google Cloud Vision OCR and Google's Gemini AI to extract structured expense data from receipt images.

## Features

- 🔍 **OCR Processing**: Uses Google Cloud Vision API for accurate text extraction
- 🤖 **AI Structuring**: Leverages Google's Gemini model to parse receipt data
- 📊 **Structured Output**: Returns standardized expense data in JSON format
- 🚀 **FastAPI**: Modern, fast web framework with automatic API documentation
- 🐳 **Docker Ready**: Containerized for easy deployment
- ☁️ **Railway Deploy**: Optimized for Railway cloud deployment

## API Endpoints

- `GET /` - Basic health check
- `GET /health` - Detailed health status with service checks
- `POST /process-receipt/` - Process receipt image and return structured data
- `GET /docs` - Interactive API documentation (Swagger UI)

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd Receipt_wala
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Google API credentials
   ```

4. **Run the server**:
   ```bash
   python api.py
   ```

The API will be available at `http://localhost:8000`

### Railway Deployment

#### Method 1: Direct GitHub Deployment

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for Railway deployment"
   git push origin main
   ```

2. **Deploy on Railway**:
   - Go to [Railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will automatically detect the configuration

3. **Set Environment Variables**:
   In Railway dashboard, go to Variables tab and add:
   ```
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
   PORT=8000
   DEBUG=false
   ```

#### Method 2: Railway CLI

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and deploy**:
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Set environment variables**:
   ```bash
   railway variables set GOOGLE_API_KEY=your_key_here
   railway variables set GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
   ```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google API key for Gemini AI |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | Path to Google Cloud service account JSON |
| `PORT` | No | Server port (default: 8000) |
| `DEBUG` | No | Enable debug mode (default: false) |

## Google Cloud Setup

1. **Create a Google Cloud Project**
2. **Enable APIs**:
   - Cloud Vision API
   - Generative AI API
3. **Create Service Account**:
   - Go to IAM & Admin → Service Accounts
   - Create new service account
   - Download JSON key file
4. **Get API Key**:
   - Go to APIs & Services → Credentials
   - Create API key for Generative AI

## API Usage

### Process Receipt

```bash
curl -X POST "https://your-app.railway.app/process-receipt/" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@receipt.jpg"
```

### Response Format

```json
{
  "amount": 25.50,
  "date": "2024-01-15T14:30:00",
  "companions": [],
  "description": "Coffee shop purchase",
  "category": "Food",
  "subcategory": "Beverages",
  "paymentMethod": "Credit Card"
}
```

## Health Monitoring

- **Basic Health**: `GET /` - Simple status check
- **Detailed Health**: `GET /health` - Comprehensive service status

## Development

### Project Structure

```
Receipt_wala/
├── api.py              # FastAPI application
├── receipt_service.py  # Core processing logic
├── config.py          # Configuration management
├── requirements.txt   # Python dependencies
├── Dockerfile        # Container configuration
├── railway.json      # Railway deployment config
└── README.md         # This file
```

### Adding Features

1. **New endpoints**: Add to `api.py`
2. **Processing logic**: Modify `receipt_service.py`
3. **Configuration**: Update `config.py`

## Troubleshooting

### Common Issues

1. **Google Credentials Error**:
   - Verify `GOOGLE_APPLICATION_CREDENTIALS` path
   - Check service account permissions

2. **API Key Issues**:
   - Ensure `GOOGLE_API_KEY` is valid
   - Check API quotas and billing

3. **Railway Deployment**:
   - Check build logs in Railway dashboard
   - Verify environment variables are set

### Debug Mode

Set `DEBUG=true` in environment variables for detailed error messages.

## License

MIT License - feel free to use this project for your own applications!

## Support

For issues and questions:
- Check the [Railway documentation](https://docs.railway.app)
- Review [Google Cloud Vision docs](https://cloud.google.com/vision/docs)
- Open an issue in this repository
