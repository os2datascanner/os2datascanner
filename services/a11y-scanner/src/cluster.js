import { Cluster } from 'puppeteer-cluster';
import { AxePuppeteer } from '@axe-core/puppeteer';
import { puppeteerConfig } from './settings.js';
import { log } from './logger.js';

const launchCluster = async () => {
    const clusterSettings = {
        concurrency: Cluster.CONCURRENCY_CONTEXT,
        maxConcurrency: 20,
    };
    if (puppeteerConfig.disable_sandbox) {
        clusterSettings.puppeteerOptions = { args: ['--no-sandbox'] };
    }
    if (puppeteerConfig.ignore_https_errors) {
        clusterSettings.puppeteerOptions = { ignoreHTTPSErrors: true };
    }

    const cluster = await Cluster.launch(clusterSettings);

    await cluster.task(async ({ page, data: url }) => {
        // TODO: Set user agent via env or as part of POST request
        await page.setUserAgent([
            'Mozilla/5.0 (X11; Linux x86_64)',
            'AppleWebKit/537.36 (KHTML, like Gecko)',
            'Chrome/81.0.4044.0',
            'Safari/537.36',
            'Magenta A11y Scanner'
        ].join(' '));

        let failure;
        page.on('requestfailed', request => {
            try {
                const errMsg = request.failure().errorText;
                log.debug("Got err: " + errMsg);
                throw new Error(errMsg);
            } catch (err) {
                log.debug("Catching err");
                failure = err;
            }
        });
        log.debug("Visiting URL: " + url);

        // TODO: Set referrer via env or as part of POST request
        await page.goto(url, {
            waitUntil: 'networkidle0',
            referrer: 'https://os2datascanner.magenta.dk',
        });

        if (failure) {
            log.debug("Rethrowing error");
            throw failure;
        }

        log.debug("Analyzing results");
        const axeResults = await new AxePuppeteer(page).analyze();
        await page.close();
        return { success: true, value: axeResults };
    });

    return cluster;
}
export { launchCluster };