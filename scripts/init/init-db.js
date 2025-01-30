db.user.insertOne({"user_id": 1, "user_status": 2})
db.user_status.insertOne({"work":0,"study":1,"personal":2,"other":3,"idle":4})
db.session_type.insertOne({"work":0,"study":1,"personal":2,"other":3})
db.session_status.insertOne({"upcoming":0,"undergoing":1,"paused":2,"completed":3})
db.focus_timer.insertOne({"user_id":1,"session_id":1,"session_status":0,"start_time":{"$date":"2025-01-27T04:18:04.725Z"},"duartion":3600,"break_time":300,"type":1,"remaining_runtime":1800,"remaining_breaktime":0})
db.block_list.insertMany([{"domain":"https://facebook.com","icon":"https://static.xx.fbcdn.net/rsrc.php/y1/r/4lCu2zih0ca.svg","list_type":4,"isActive":true},{"domain":"https://youtube.com","icon":"","list_type":2,"isActive":false}])
db.focus_time_summary.insertOne({"user_id":1,"daily_total":2,"weekly_total":7,"lifetime_total":43.5,"daily":[{"type":0,"duration":2}],"weekly":[{"type":0,"duration":37.5},{"type":2,"duaration":5}]})



