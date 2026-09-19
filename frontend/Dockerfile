FROM node:22-alpine

ENV NODE_ENV=production

WORKDIR /app

COPY package.json ./
COPY pnpm-lock.yaml ./
COPY node_modules ./node_modules
COPY .next ./.next

EXPOSE 3000

CMD ["node_modules/.bin/next", "start", "-p", "3000"]
