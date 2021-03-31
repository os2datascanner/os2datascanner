FROM node:15-slim

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y wget gnupg ca-certificates \
      --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y gpg google-chrome-stable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 \
      --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install tini for a proper init process
RUN url=https://github.com/krallin/tini/releases/download/v0.18.0 \
    && wget -qO /usr/local/bin/tini ${url}/tini-amd64 \
    && chmod +x /usr/local/bin/tini \
    # Add puppeteer user
    && groupadd --system --gid 74010 puppeteeruser && useradd --system --gid 74010 --uid 74010 --groups audio,video puppeteeruser

# Create app directory
WORKDIR /srv

# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
COPY ./package*.json .
# Install from lockfile
RUN npm ci --only=production

# Bundle app source
COPY ./src .

EXPOSE 8888

# Run everything after as non-privileged user.
USER puppeteeruser

ENTRYPOINT ["tini", "--"]
CMD [ "node", "server.js" ]
