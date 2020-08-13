# def upload_field_and_conferences():
#     import json
#     from kcss.models import Author

#     korean_prob_dict = json.load(open("./kcss/static/json/kr_prob_dict.json"))
#     woman_prob_dict = json.load(open("./kcss/static/json/gender_dict.json"))

#     for author_name in korean_prob_dict.keys():
#         korean_prob = korean_prob_dict[author_name]
#         if author_name in woman_prob_dict:
#             woman_prob = woman_prob_dict[author_name]
#         else:
#             woman_prob = 0
#         name_parts = author_name.split()
#         first_name = " ".join(name_parts[:-1])
#         last_name = name_parts[-1]
#         author = Author(
#             first_name=first_name,
#             last_name=last_name,
#             korean_prob=korean_prob,
#             woman_prob=woman_prob,
#         )
#         author.save()
