from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str


class QBoundReq(BaseModel):
    username: str
    model_name: str
    model: str

class expDataRequest(BaseModel):
    username: str
    experiment_name: str
    upload_date: str
    experiment_noise_date: str
    experiment_data: str
    experiment_circuit: str

class IBMConfig(BaseModel):
    user: str
    IBM_API_token: str
    backend_name: str
    Time_delta: int  
    Start_date: str
    End_date: str
    Training_epochs: int
    # Model_config: dict[str, Any]  # Captures the nested configuration
    dataset_split: float          # Usually a decimal like 0.8
    number_samples: int
    result_file_name: str
    save_file_name: str
    exec_mode: str
    compression: bool             # Assuming True/False, change to str if it's a method
    # hardware_settigs: dict[str, Any] # Note: kept your spelling 'settigs' to match the JSON