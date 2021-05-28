import { generateEARLReport } from '@qualweb/earl-reporter';
import { Evaluation } from '@qualweb/evaluation';
import { log } from './logger.js';
import fetch from 'node-fetch';

const qualwebTask = async ({ page, data: url }) => {
    await page.setUserAgent([
        'Mozilla/5.0 (X11; Linux x86_64)',
        'AppleWebKit/537.36 (KHTML, like Gecko)',
        'Chrome/81.0.4044.0',
        'Safari/537.36',
        'Magenta A11y Scanner'
    ].join(' '));

    const modulesToExecute = {
        act: true,
        wcag: true,
        bp: true,
        wappalyzer: false,
        counter: false
    };

    // See https://github.com/qualweb/core#options
    const qualwebOptions = {
        'act-rules': {},
        'wcag-techniques': {},
    };

    const magentaSystemDefinition = {
        'name': 'OS2Datascanner',
        'description': 'OS2Datascanner A11y Scanner powered by QualWeb',
        'version': '0.0.1',
        'homepage': 'https://os2datascanner.magenta.dk'
    };

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

    let response = await page.goto(url, {
        waitUntil: 'networkidle0',
        referrer: 'https://os2datascanner.magenta.dk',
    });

    if (failure) {
        log.debug("Rethrowing error");
        throw failure;
    }
    const sourceHeadContent = await fetch(url)
	.then(res => res.text())
	.then(body => {
        const htmlText = body.trim();
        return htmlText.includes('<head>') ? htmlText.split('<head>')[1].split('</head>')[0].trim() : '';
    });

    log.debug("Creating evaluation");
    const evaluation = new Evaluation(url, page, modulesToExecute);

    log.debug("Generating evaluation report");
    const evaluationReport = await evaluation.evaluatePage(sourceHeadContent, qualwebOptions, null);

    log.debug("Generating EARL report");
    // The public interface expects a list of evaluations (and returns a list)
    evaluationReport['system'] = magentaSystemDefinition;
    const reports = generateEARLReport([evaluationReport], null);
    const report = reports[0];

    await page.close();
    return { success: true, value: report };
};

export { qualwebTask };
