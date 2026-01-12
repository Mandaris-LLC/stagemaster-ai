import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
});

export const uploadImage = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/images/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
};

export const createStagingJob = async (imageId, roomType, stylePreset, options = {}) => {
    const response = await api.post('/jobs', {
        image_id: imageId,
        room_type: roomType,
        style_preset: stylePreset,
        fix_white_balance: options.fixWhiteBalance ?? true,
        wall_decorations: options.wallDecorations ?? true,
    });
    return response.data;
};

export const getJobStatus = async (jobId) => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
};

export default api;
