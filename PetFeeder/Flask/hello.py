from ultralytics import YOLO

# Load the YOLO model
model = YOLO("yolov8n.pt")

# Print model details
print(model.names)
print(model.info())
print(model.model)


 # Evaluate model on validation dataset
# metrics = model.val()

 # Print metrics for all classes
# print("Class-wise Accuracy:")
# for class_id, class_name in model.names.items():
#     print(f"Class {class_id} ({class_name}): AP = {metrics['ap50'][:, class_id].mean():.2f}")
