FROM node:24.18.0-alpine3.24 AS build

WORKDIR /workspace

RUN corepack enable && corepack prepare pnpm@11.13.0 --activate

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps ./apps
COPY packages ./packages

RUN pnpm install --frozen-lockfile
RUN pnpm --filter @kinward/web... build

FROM nginx:1.29.8-alpine3.23 AS runtime

COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/web/dist /usr/share/nginx/html

EXPOSE 8080
