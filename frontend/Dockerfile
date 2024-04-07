FROM node:18.2.0 AS build-step
WORKDIR /app
COPY package.json yarn.lock .npmrc ./
RUN yarn install
RUN test -e .env || cp .env.example .env
COPY . .
RUN yarn build
EXPOSE 5000
CMD ["yarn", "preview"]
