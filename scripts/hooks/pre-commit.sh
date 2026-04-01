#!/bin/bash

# Function to get current timestamp and branch
get_new_local_version_string() {
    local timestamp=$(date -u +"%Y.%m.%dT%H.%M.%S.%3NZ")
    local commit_hash=$(git rev-parse --short HEAD)
    local branch=$(git rev-parse --abbrev-ref HEAD | tr '/' '.' | tr '-' '.' | tr '_' '.')
    echo "${timestamp}.${commit_hash}.${branch}"
}

# Function to find relevant VERSION files based on changed paths
find_version_files() {
    local changed_files=$(git diff --cached --name-only)
    local project_root=$(git rev-parse --show-toplevel)
    local version_files=("$project_root/VERSION")

    # Function to find the nearest VERSION file within the project root
    find_nearest_version_file() {
        local dir="$1"
        while [[ "$dir" != "$project_root" && "$dir" != "/" ]]; do
            if [[ -f "$dir/VERSION" ]]; then
                echo "$dir/VERSION"
                return
            fi
            dir=$(dirname "$dir")
        done

        # Fallback to root VERSION file if none found and it exists
        echo "$project_root/VERSION"
    }

    # Process changed files line-by-line
    while IFS= read -r file; do
        local file_dir=$(dirname "$file")
        local nearest_version_file=$(find_nearest_version_file "$file_dir")

        # Add the VERSION file if it's found and not already in the list
        if [[ -n "$nearest_version_file" ]] && [[ ! " ${version_files[@]} " =~ " ${nearest_version_file} " ]]; then
            version_files+=("$nearest_version_file")
        fi
    done < <(echo "$changed_files")

    printf "%s\n" "${version_files[@]}"
}

# Main versioning logic
update_version_files() {
    local version_string=$(get_new_local_version_string)
    local version_files=$(find_version_files)

    # Update each relevant VERSION file
    while IFS= read -r file; do
        # Extract semantic version from file
        base_version=$(sed -n 's/\(.*\)+.*/\1/p' "$file")

        # Prepend the semantic version to local version
        new_version_string="$base_version+$version_string"

        echo "$new_version_string" > "$file"
        git add "$file"
    done < <(echo "$version_files")
}

# Run the versioning update
update_version_files

exit 0
