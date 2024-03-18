FROM node:18.2.0 AS build-step
WORKDIR /build
COPY package.json yarn.lock .npmrc ./
RUN yarn install
COPY . .
RUN test -e .env || cp .env.example .env
ENV NODE_OPTIONS="--max-old-space-size=6144"
RUN yarn build:prod

FROM node:18.2.0
WORKDIR /app
COPY --from=build-step /build/dist /app/dist
COPY --from=build-step /build/server /app
COPY --from=build-step /build/start.sh /app/start.sh
COPY --from=build-step /build/.env* /app/
RUN yarn install
EXPOSE 5000
ENV ENVIRONMENT_NAME=default
ENTRYPOINT ["node","server.js"]
