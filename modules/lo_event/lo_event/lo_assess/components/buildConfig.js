import path from 'path';
import { fileURLToPath } from 'url';

export function getTemplatePath(templateFileName) {
  const moduleDir = path.dirname(fileURLToPath(import.meta.url));
  const parentDir = path.join(moduleDir, '..');
  return path.join(parentDir, templateFileName);
}

const _baseConfig = {
  loa: {
    jsPattern: './lo_event/lo_assess/components/**/{[A-Z]*,use[A-Z]*}.jsx',
    xmlPattern: './lo_event/lo_assess/components/**/[A-Z]*.xml',
    componentsFile: "./lo_event/lo_assess/components/components.jsx",
  },
  next: {
    compileDestination: "./src/app/compiledComponents/",
    componentXMLPattern: "./xml/components/**/*.xml",
    nextPageXMLPattern: "./xml/pages/**/*.xml",
    nextComponentFile: "./src/app/compiledComponents.js",
    nextPageTarget: "./src/app/{{page}}/page.js",
    nextPageDir: "./src/app/{{page}}/page.js",
  },
  templateLocations: {
    componentFile: getTemplatePath("component.jsx.template"),
    pageFile: getTemplatePath("pages.jsx.template"),
  }
};

export const config = () => _baseConfig;
