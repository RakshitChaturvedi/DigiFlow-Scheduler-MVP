import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'http://127.0.0.1:8000', // API base URL
    withCredentials: true
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
    (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (
            error.response?.status === 401 &&
            !originalRequest._retry &&
            !originalRequest.url.includes('/auth/refresh') &&
            !originalRequest.url.includes('/auth/login')
        ) {
            originalRequest._retry = true;

            try {
                const res = await axios.post('http://127.0.0.1:8000/api/auth/refresh', {}, {
                    withCredentials: true
                });

                const newToken = res.data.access_token;
                localStorage.setItem('accessToken', newToken);
                apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
                originalRequest.headers['Authorization'] = `Bearer ${newToken}`;

                return apiClient(originalRequest); // retry original request
            } catch (refreshError) {
                localStorage.removeItem('accessToken');
                window.location.href = '/login'; // redirect to login
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);        
    }
);

export const getProductionOrders = async (params = {}) => {
  const response = await axios.get('/orders/', { params });
  return response.data;
};

export default apiClient