import logger from 'loglevel';
import { loglevel } from './settings.js';

logger.setLevel(loglevel);
export const log = logger;