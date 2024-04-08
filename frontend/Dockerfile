FROM node:18.2.0 AS build-step
WORKDIR /build
COPY . .
RUN yarn install
RUN test -e .env || cp .env.example .env
RUN yarn build

FROM node:18.2.0 AS production-stage
RUN npm install -g serve
WORKDIR /app
COPY --from=build-step /build/dist /app/dist
EXPOSE 5000
CMD ["serve", "-s", "dist", "-l", "5000"]
