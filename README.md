<div align="center">

# Jetson Face Auth

</div>

This is my first project on jetson

What this program does is basicly log when people get out and get in the building, and stop strangers from getting in the building

<details open>
<summary><strong>Training</strong></summary>

I trained `efficientnet_v2_s` with a dataset with 300 picture of each person for 250 epochs.

#### Training the model
1. download scripts from `https://github.com/dusty-nv/pytorch-clboldassification`
2. add parameters
    ```
    arch=efficientnet_v2_s
    pretrained=False
    ```
3. Run
</details>

<details open>
<summary><strong>Run the program</strong></summary>

1. Put model file `.onnx` and `labels.txt` in directory `./models`
2. Rename your model to `target.onnx`
3. Run 
    ```shell
    python3 app.py
    ```
4. Access `http://<jetson-ip>:8050` from browser ()

</details>