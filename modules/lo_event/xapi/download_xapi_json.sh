# TODO: Remove original files, keep only the nicely formatted .json ones
# TODO: Consider moving into Python and main tool

wget https://registry.tincanapi.com/api/v1/uris/verb
wget https://registry.tincanapi.com/api/v1/profile
wget https://registry.tincanapi.com/api/v1/uris/extension
wget https://registry.tincanapi.com/api/v1/uris/attachmentUsage
wget https://registry.tincanapi.com/api/v1/uris/activityType

files=("verb" "profile" "extension" "attachmentUsage" "activityType")

for file in "${files[@]}"
do
  python -c "import json; json.dump(json.load(open('${file}')), open('${file}.json', 'w'), indent=2)"
done
