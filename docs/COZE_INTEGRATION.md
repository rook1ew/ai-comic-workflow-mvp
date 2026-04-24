# Coze Integration

Coze should orchestrate the early workflow and call this backend through high-level APIs.

Recommended flow:

1. Coze collects project inputs from the user.
2. Coze calls `POST /coze/project/init`.
3. Coze generates or requests a script through `generate-script`.
4. Coze generates storyboard data through `generate-storyboard`.
5. Coze triggers `create-asset-tasks`.
6. Backend executes mock providers and returns structured results.
7. Coze shows next action to the user.
