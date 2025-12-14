import axios from 'axios';
import { config } from './config';

const client = axios.create({
    baseURL: config.MAESTRO_API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface ChatResponse {
    message: string;
    agent: string;
    session_id: string;
    route: string;
    data?: any; // For future usage if backend sends extra data
}

export const api = {
    sendMessage: async (message: string, userId: string, sessionId?: string): Promise<ChatResponse> => {
        const response = await client.post<ChatResponse>('/chat', {
            message,
            user_id: userId,
            session_id: sessionId,
        });
        return response.data;
    },
};
