FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json angular.json tsconfig*.json ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npx ng build --configuration production --base-href=/

FROM nginx:alpine

RUN rm -rf /usr/share/nginx/html/*
RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist/angular-frontend/browser /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
