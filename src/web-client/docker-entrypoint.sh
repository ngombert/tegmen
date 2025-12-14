#!/bin/sh

# Inject environment variables into config.js
echo "window.env = {" > /usr/share/nginx/html/config.js
echo "  MAESTRO_API_URL: \"${MAESTRO_API_URL:-http://localhost:8000}\"," >> /usr/share/nginx/html/config.js
echo "};" >> /usr/share/nginx/html/config.js

# Start Nginx
exec nginx -g "daemon off;"
