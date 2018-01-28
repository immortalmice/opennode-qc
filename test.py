import datetime, time

a = datetime.datetime.now();
print(a)
time.sleep(0.52);
b = datetime.datetime.now();
print(b)
print((b-a).microseconds)
