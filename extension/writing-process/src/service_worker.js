// Combining the two background scripts into one to serve
// as a single service worker script

try {
    importScripts("./writing_common.js", "./background.js");
} catch (e) {
    console.log(e);
}
