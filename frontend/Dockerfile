# Build Stage
FROM node:18.2.0 AS build-step
WORKDIR /build
COPY . .

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy environment variables file if it doesn't exist
RUN test -e .env || cp .env.example .env

ARG VITE_USE_RELATIVE_BASE_URL
ARG VITE_DOCS_QA_STANDALONE_PATH
ARG VITE_QA_FOUNDRY_URL
ARG VITE_USE_LOCAL
ARG VITE_GTAG_ID
ENV VITE_USE_RELATIVE_BASE_URL=${VITE_USE_RELATIVE_BASE_URL} \
    VITE_DOCS_QA_STANDALONE_PATH=${VITE_DOCS_QA_STANDALONE_PATH}
RUN if [ -n "$VITE_QA_FOUNDRY_URL" ]; then \
    export VITE_QA_FOUNDRY_URL=${VITE_QA_FOUNDRY_URL}; \
    fi
RUN if [ -n "$VITE_USE_LOCAL" ]; then \
    export VITE_USE_LOCAL=${VITE_USE_LOCAL}; \
    fi
RUN if [ -n "$VITE_GTAG_ID" ]; then \
    export VITE_GTAG_ID=${VITE_GTAG_ID}; \
    fi

# Build the project
RUN yarn build

# Production Stage
FROM node:18.2.0 AS production-stage
RUN npm install -g serve
WORKDIR /app
COPY --from=build-step /build/dist /app/dist

EXPOSE 5000
CMD ["serve", "-s", "dist", "-l", "5000"]
