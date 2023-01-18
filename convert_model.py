import json

if __name__ == "__main__":
    with open("./models_old.json") as f:
        j = json.load(f)["models"]
    o = {"stable_diffusion":[], "textual_inversion_embedding":[], "vae":[], "hypernetwork":[], "aesthetic_embedding":[]}
    for i in j:
        for k in o:
            if k in i["tags"]:
                o[k].append({"name":i["name"], "url":i["url"], "description":i["description"]})
    print(o)
    with open("./models.json", "w") as f:
        json.dump(o, f)
