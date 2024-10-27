<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/icon-dark.png">
    <img src="./assets/icon-light.png" width="150">
  </picture>
</p>

# BasketRadar

Enhancing Defensive Strategies Through Visualization 

## Deployment Workflows

### [Deploy Webapp to Azure](https://github.com/willcoughlin/basketradar/actions/workflows/deploy-webapp.yaml)

<details>
<summary>See info</summary>

* Deploys contents of `webapp` folder to Azure Web Apps.
* Requires Dash app server to be assigned to variable called `app` in `app.py` file:
  ```python
  dash_app = Dash()
  app = dash_app.server
  ```
* Run by selecting workflow in "Actions" tab, clicking "Run Workflow", and selecting a branch to deploy.
  ![image](https://github.com/user-attachments/assets/ada31af2-8917-46f4-88bb-c2e3e4daa9cc)

</details>

### [Fetch and Push Data to Azure](https://github.com/willcoughlin/basketradar/actions/workflows/fetch-and-push-data.yaml)

<details>
<summary>See info</summary>

* Runs `load_and_clean_data.py` script in `data_processing` folder, uploading its output to Azure Blob Storage.
* Requires script to write data to upload into the `data` folder within `data_processing`.
* Will not upload all raw data from Kaggle.
* Run by selecting workflow in "Actions" tab, clicking "Run Workflow", and selecting a branch with the version of the script you'd like to run.
  ![image](https://github.com/user-attachments/assets/7c0c6641-1601-4ed0-84ad-eeb30a845138)

</details>
