FROM node:18.2.0 AS build-step
WORKDIR /build
COPY . .
RUN yarn install
RUN test -e .env || cp .env.example .env
ARG VITE_USE_RELATIVE_BASE_URL VITE_PATH_BASED_ROUTING_ENABLED
ENV VITE_USE_RELATIVE_BASE_URL=${VITE_USE_RELATIVE_BASE_URL} \
    VITE_PATH_BASED_ROUTING_ENABLED=${VITE_PATH_BASED_ROUTING_ENABLED}
RUN yarn build

FROM node:18.2.0 AS production-stage
RUN npm install -g serve
WORKDIR /app
COPY --from=build-step /build/dist /app/dist
EXPOSE 5000
CMD ["serve", "-s", "dist", "-l", "5000"]
