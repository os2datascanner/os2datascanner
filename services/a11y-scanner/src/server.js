'use strict';

import express, { json } from 'express';
import basicAuth from 'express-basic-auth';
import { serverConfig as settings } from './settings.js';
import { log } from './logger.js';
import { launchCluster } from './cluster.js';
import { qualwebTask } from './tasks.js';

log.info("Starting up...");

// Constants
const HOST = settings.host;
const PORT = settings.port;
const USER = settings.user;
const PASSWORD = settings.password;

// Sanity checks
if (!USER) {
    log.error("No user setting specified. Exiting");
    process.exit(1);
}

if (!PASSWORD) {
    log.error("No password setting specified. Exiting");
    process.exit(1);
}

// App
const app = express();
app.use(basicAuth({
    users: { [USER]: PASSWORD },
}));

app.use(json({ "limit": 10 * 1024 * 1024 }));

let cluster = await launchCluster();

app.post('/qualweb', async (req, res) => {
    log.debug("Got POST request on /qualweb");
    if (!req.body.url) {
        res.status(400).json( { error: "Must provide URL in request"});
        return;
    }
    try {
        const result = await cluster.execute(req.body.url, qualwebTask).catch(err => { throw err; });
        log.debug("Sending response");
        res.json({ data: result.value });
    } catch (err) {
        log.debug("Sending error response");
        res.json({ error: err.message });
    }
});

app.post('/axe', async (req, res) => {
    log.debug("Got POST request on /axe");
    if (!req.body.url) {
        res.status(400).json( { error: "Must provide URL in request"});
        return;
    }
    try {
        const result = await cluster.execute(req.body.url).catch(err => { throw err; });
        log.debug("Sending response");
        res.json({ data: result.value });
    } catch (err) {
        log.debug("Sending error response");
        res.json({ error: err.message });
    }
});



app.listen(PORT, HOST);
log.info(`Running on http://${HOST}:${PORT}`);
