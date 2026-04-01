# writing-process

Tracks writing in Google Docs, and provides nifty insights to you and your teachers!

## Development

This extension directory structure was created with [Extension CLI](https://oss.mobilefirst.me/extension-cli/).
The original extension, which was just a handful of javascript files, were then copied into the structure.

### To Begin

To get started, run the following:

```bash
cd extention/writing-process
npm install
```

### Available Commands

We created these commands:

| Commands | Description |
| --- | --- |
| `npm run bundle` | runs webpack to bundle dependencies into code |
| `npm run build` | cleans dist folder, bundles code, then runs ext:build |

In addition, for reference, we kept the following commands from `extension-cli`:

| Commands | Description |
| --- | --- |
| `npm run ext:start` | builds extension into `dist/`, watches for file changes |
| `npm run ext:build` | generate release version - `release.zip` |
| `npm run ext:docs` | generate source code docs into `public/documentation` |
| `npm run ext:clean` | removes `dist/` directory |
| `npm run ext:test` | run unit tests |
| `npm run ext:sync` | update projects config files for `extension-cli` |

For CLI instructions see [User Guide &rarr;](https://oss.mobilefirst.me/extension-cli/)

### Learn More

#### Extension Developer guides

- [Getting started with extension development](https://developer.chrome.com/extensions/getstarted)
- Manifest configuration: [version 3](https://developer.chrome.com/docs/extensions/mv3/intro/)
- [Permissions reference](https://developer.chrome.com/extensions/declare_permissions)
- [Chrome API reference](https://developer.chrome.com/docs/extensions/reference/)

#### Extension Publishing Guides

- [Publishing for Chrome](https://developer.chrome.com/webstore/publish)
