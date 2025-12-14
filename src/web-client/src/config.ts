export const config = {
    MAESTRO_API_URL: window.env?.MAESTRO_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000',
};
