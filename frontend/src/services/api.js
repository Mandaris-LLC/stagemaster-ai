import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
});

export const uploadImage = async (file, roomId = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (roomId) {
        formData.append('room_id', roomId);
    }
    const response = await api.post('/images/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: roomId ? { room_id: roomId } : {}
    });
    return response.data;
};

export const createStagingJob = async (imageId, roomType, stylePreset, options = {}) => {
    const response = await api.post('/jobs', {
        image_id: imageId,
        room_type: roomType,
        style_preset: stylePreset,
        fix_white_balance: options.fixWhiteBalance ?? false,
        wall_decorations: options.wallDecorations ?? true,
        include_tv: options.includeTV ?? false,
        room_id: options.roomId,
    });
    return response.data;
};

export const listProperties = async () => {
    const response = await api.get('/properties');
    return response.data;
};

export const createProperty = async (data) => {
    const response = await api.post('/properties', data);
    return response.data;
};

export const getProperty = async (propertyId) => {
    const response = await api.get(`/properties/${propertyId}`);
    return response.data;
};

export const createRoom = async (propertyId, data) => {
    const response = await api.post(`/properties/${propertyId}/rooms`, data);
    return response.data;
};

export const getRoom = async (roomId) => {
    const response = await api.get(`/properties/rooms/${roomId}`);
    return response.data;
};

export const deleteImage = async (imageId) => {
    const response = await api.delete(`/images/${imageId}`);
    return response.data;
};

export const deleteRoom = async (roomId) => {
    const response = await api.delete(`/properties/rooms/${roomId}`);
    return response.data;
};

export const getJobStatus = async (jobId) => {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
};

export default api;
