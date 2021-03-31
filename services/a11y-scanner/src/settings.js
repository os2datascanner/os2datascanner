const serverConfig = {
    user: process.env.A11Y_SCANNER_USERNAME || null,
    password: process.env.A11Y_SCANNER_PASSWORD || null,

    host: process.env.A11Y_SCANNER_HOST || "0.0.0.0",
    port: process.env.A11Y_SCANNER_PORT || 8888,

};

const puppeteerConfig = {
    disable_sandbox: process.env.A11Y_SCANNER_DISABLE_SANDBOX || false,

    ignore_https_errors: process.env.A11Y_SCANNER_IGNORE_HTTPS_ERRORS || false,
}

const loglevel = process.env.A11Y_SCANNER_LOGLEVEL || "warn";

export {
    serverConfig,
    puppeteerConfig,
    loglevel,
};
