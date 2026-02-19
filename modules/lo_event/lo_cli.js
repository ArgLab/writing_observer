#!/usr/bin/env node

import * as bl from './lo_event/lo_assess/components/buildlib.js';
import { config } from './lo_event/lo_assess/components/buildConfig.js';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

console.log("Welcome to the lo_cli!");

// Define the command-line options using yargs
const argv = yargs(hideBin(process.argv))
      .command('build', 'Build JSX files from XML, in lo_assess', (argv) => {
        console.log("Building LO Assess Components!", argv);
        bl.compileXMLComponents();
        const cfs = bl.writeComponentFile();
        console.log("Wrote:\n", cfs);
      })
      .command('info', 'See what we would build', (args) => {
        console.log(bl.componentsFile);
        console.log(config());
        console.log(bl.listXmlFiles());
        console.log(bl.listComponentFiles());
      })
      .command('build_next', 'Build JSX files from XML, in a child project', (argv) => {
        console.log("Building Local Components");
      })
      .demandCommand(1, "Please provide a command")
      .help()
      .argv;

