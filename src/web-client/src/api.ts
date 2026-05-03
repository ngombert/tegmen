import axios from 'axios';
import { config } from './config';

const client = axios.create({
    baseURL: config.MAESTRO_API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor to inject the token if present
client.interceptors.request.use((req) => {
    const token = localStorage.getItem('tegmen_token');
    if (token) {
        req.headers.Authorization = `Bearer ${token}`;
    }
    return req;
});

export interface JsonRpcResponse<T = any> {
    jsonrpc: "2.0";
    result?: T;
    error?: {
        code: number;
        message: string;
        data?: any;
    };
    id: string | number;
}

export interface ChatResult {
    message: string;
    agent: string;
    route: string;
    _debug?: any;
}

export const api = {
    // Development utility to get a token
    getDevToken: async (userId: string): Promise<string> => {
        const response = await client.get(`/dev/token/${userId}`);
        const token = response.data.access_token;
        localStorage.setItem('tegmen_token', token);
        return token;
    },

    sendMessage: async (message: string, sessionId?: string): Promise<ChatResult> => {
        const payload = {
            jsonrpc: "2.0",
            method: "message/send",
            params: {
                message: message,
                debug: true // Always request debug info in dev web client
            },
            id: sessionId || Math.random().toString(36).substring(7)
        };

        const response = await client.post<JsonRpcResponse<ChatResult>>('/api/v1/routing', payload);
        
        if (response.data.error) {
            throw new Error(response.data.error.message);
        }

        if (!response.data.result) {
            throw new Error("Réponse vide de Maestro");
        }

        return response.data.result;
    },
};
