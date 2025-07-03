import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'http://127.0.0.1:8000', // API base URL
});

// Use an interceptor to attach the token to every request
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default apiClient