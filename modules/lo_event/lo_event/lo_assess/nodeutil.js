// There is a mess with package managers. For ease, to switch to
// require, replace the imports with:
//
// const fs = require('fs');
// const xml2js = require('xml2js');
//
// And then change parseString to xml2js.parseString

import fs from 'fs';
import path from 'path';
import glob from 'glob';

/*
 * Helpful test functions. Some of these might transition into the
 * final system, and some might go away.
 */

export function printDirs() {
  console.log('Current working directory:', process.cwd());
  console.log('Program directory:', path.dirname(process.argv[1]));
  console.log('File directory:', path.dirname(import.meta.url));
  console.log('Module directory:', path.dirname(import.meta.url));
}

export function findFiles(basedir, callback) {
  glob.sync(`${basedir}/**/*.xml`).forEach((xmlName) => {
    const baseName = path.basename(xmlName, ".xml");
    const jsxName = path.join(path.dirname(xmlName), `${baseName}.jsx`);
    console.log(xmlName, baseName, jsxName);
    if(callback) {
      callback(xmlName, jsxFile);
    }
    //const xmlContent = fs.readFileSync(xmlFile, "utf8");
    //fs.writeFileSync(jsxFile, jsxContent, "utf8");
  });
}

export async function inspectModule(modulePath) {
  const module = await import(modulePath);
  return Object.keys(module);
}
