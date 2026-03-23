import requests
import json
from pyfcm import FCMNotification



def send_push(titulo, mensaje, receiver):
  push_service = FCMNotification(
      api_key="AAAAREoXibc:APA91bFNNnBNjaAsT0jxa1qQOtJ0eIjRYkQwWdhluYbYEP2N4NR49PNrb80cNCVOFIe1z2YKtoLd7gOWHZNqUNuuhVIz-orlTdpinlKhNiBLvh4O1GVd_G5Cie61fmkDm1YtnvCfK3h7"
    )

  registration_id = receiver
  message_title = titulo
  message_body = mensaje
  icon_message = "https://s3.amazonaws.com/miurabox/testing/zgc/logo_miura.jpeg"
  sound = "https://s3.amazonaws.com/miurabox/testing/zgc/notification.wav"



  data_message = {
      "chat" : True,
  }
  try:
    result = push_service.notify_single_device(
      registration_id=registration_id, 
      message_title=message_title, 
      message_body=message_body, 
      message_icon = icon_message,
      content_available=True, 
      data_message=data_message

    )
  except Exception as e:
    pass

  # Send to multiple devices by passing a list of ids.
  # registration_ids = ["<device registration_id 1>", "<device registration_id 2>", ...]
  # message_title = "Uber update"
  # message_body = "Hope you're having fun this weekend, don't forget to check today's news"
  # result = push_service.notify_multiple_devices(registration_ids=registration_ids, message_title=message_title, message_body=message_body)



# def send_push(request, titulo, mensaje, receiver):
#     url = "https://fcm.googleapis.com/fcm/send"
#     payload = "{\"notification\": {\"title\": \"%s\",\"body\": \"%s\",\"icon\": \"https://s3.amazonaws.com/miurabox/testing/zgc/logo_miura.jpeg\"},\"webpush\": {\"headers\": {\"Urgency\": \"high\"}}, \"to\": \"%s\"}" %(titulo,mensaje,receiver)

#     # headers = "{Content-Type: application/json,Authorization: key=AAAAREoXibc:APA91bFNNnBNjaAsT0jxa1qQOtJ0eIjRYkQwWdhluYbYEP2N4NR49PNrb80cNCVOFIe1z2YKtoLd7gOWHZNqUNuuhVIz-orlTdpinlKhNiBLvh4O1GVd_G5Cie61fmkDm1YtnvCfK3h7}"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": "key=AAAAREoXibc:APA91bFNNnBNjaAsT0jxa1qQOtJ0eIjRYkQwWdhluYbYEP2N4NR49PNrb80cNCVOFIe1z2YKtoLd7gOWHZNqUNuuhVIz-orlTdpinlKhNiBLvh4O1GVd_G5Cie61fmkDm1YtnvCfK3h7"
#     }
#     r = requests.post(url,data=payload,headers=headers)
#     response = json.loads(r.text)
#     return(r)


