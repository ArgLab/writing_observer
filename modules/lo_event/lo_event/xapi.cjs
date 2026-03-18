// TODO: All of this needs better function names, comments, etc.
//
// We want a general code cleanup.

const activityTypeApi = require('../xapi/activityType.json');
const attachmentUsageApi = require('../xapi/attachmentUsage.json');
const extensionApi = require('../xapi/extension.json');
const profileApi = require('../xapi/profile.json');
const verbApi = require('../xapi/verb.json');

function aaevSelector (t) {
  const nameField = t.metadata.metadata.name;
  return nameField['en-US'] || nameField['en-us'];
}

function cleanName (n) {
  return n.toUpperCase().trim().replace(/ |-|\./g, '_').replace(/[()]/g, '');
}

function toDicts (jsonBlock, selector, namesDict, objectsDict) {
  for (let i = 0; i < jsonBlock.length; i++) {
    const name = cleanName(selector(jsonBlock[i]));
    namesDict[name] = name;
    objectsDict[name] = jsonBlock[i];
  }
}

const ACTIVITYTYPE = {};
const ActivityTypeObjects = {};
toDicts(activityTypeApi, aaevSelector, ACTIVITYTYPE, ActivityTypeObjects);

const ATTACHMENTUSAGE = {};
const AttachmentUsageObjects = {};
toDicts(attachmentUsageApi, aaevSelector, ATTACHMENTUSAGE, AttachmentUsageObjects);

const EXTENSION = {};
const ExtensionObjects = {};
toDicts(extensionApi, aaevSelector, EXTENSION, ExtensionObjects);

const PROFILE = {};
const ProfileObjects = {};
toDicts(profileApi, (t) => t.name, PROFILE, ProfileObjects);

const VERB = {};
const VerbObjects = {};
toDicts(verbApi, aaevSelector, VERB, VerbObjects);

module.exports = {
  ACTIVITYTYPE,
  ActivityTypeObjects,
  ATTACHMENTUSAGE,
  AttachmentUsageObjects,
  EXTENSION,
  ExtensionObjects,
  PROFILE,
  ProfileObjects,
  VERB,
  VerbObjects
};
