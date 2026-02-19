FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY . .
RUN npm run build

FROM node:20-alpine

RUN npm install -g serve

COPY --from=builder /app/dist /app/dist

EXPOSE 3000

CMD ["serve", "-s", "/app/dist", "-l", "3000"]
