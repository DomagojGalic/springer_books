import os
import requests

from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

entryFolderName = "books"
pdf = True
epub = False


def makeFolder(folderName):
    if not os.path.exists(folderName):
        os.mkdir(folderName)
    elif not os.path.isdir(folderName):
        raise FileExistsError("File of name {}".format(folderName))

def nameSanitizer(name):
    newName = "_".join(name.replace(",", "").replace(".", "").replace(
        "'", "").replace(";", "").replace("/", "").lower().split())
    return newName

def bookAuthorSanitizer(name):
    newName = "_".join([i.split()[-1].lower() for i in name.split(",")])
    return newName

def makeFolderStructure(df, entryFolderName):
    makeFolder(entryFolderName)
    folderDict = {i: os.path.join(entryFolderName, nameSanitizer(i))
        for i in df.loc[:, "English Package Name"].unique()}
    for  value in folderDict.values():
        makeFolder(value)
    return folderDict

def writeContent(row, content, bookType):
    link = "https://link.springer.com/" + content
    response = requests.get(link).content
    name = "{}.{}".format(row.full_path, bookType)
    with open(name, "wb") as f:
        f.write(response)

def downloadAndSave(row, pdf = True, epub = True):
    if (os.path.exists(row.full_path + ".pdf") == pdf) and (os.path.exists(row.full_path + ".epub") == epub):
        return
    response = requests.get(row.OpenURL)
    soup = BeautifulSoup(response.content, features = "lxml")
    anchorTags = soup.findAll("a", title = True, href = True)
    pdfContentList = [tag["href"] for tag in anchorTags if "download this book in pdf format" in tag["title"].lower()]
    epubContentList = [tag["href"] for tag in anchorTags if "download this book in epub format" in tag["title"].lower()]
    
    if pdfContentList and pdf:
        writeContent(row, pdfContentList[0], "pdf")
    
    if epubContentList and epub:
        writeContent(row, epubContentList[0], "epub")
    

def main(xlsxPath = "Free+English+textbooks.xlsx",
        entryFolderName = entryFolderName,pdf = pdf, epub = epub):
    df = pd.ExcelFile(xlsxPath).parse()

    failed = []

    pathsDict = makeFolderStructure(df, entryFolderName)
    df.loc[:, "path_save"] = df.loc[:, "English Package Name"].map(pathsDict)
    df.loc[:, "name_save"] = df.loc[:, "Book Title"].apply(nameSanitizer)
    df.loc[:, "author_save"] = df.loc[:, "Author"].apply(bookAuthorSanitizer)
    df.loc[:, "full_path"] = df.apply(lambda x: os.path.join(
        x.path_save, "{}-{}".format(x.author_save, x.name_save)),axis = 1)

    length = len(df)
    pbar = tqdm(df.iterrows(), total = length)
    for i, row in pbar:
        pbar.set_description("Downloading... {} [{}]".format(row.loc["Book Title"], row.loc["English Package Name"]))
        try:
            downloadAndSave(row, pdf, epub)
        except:
            failed.append(i)
    
    print("Success: {}\nFail: {}".format(length - len(failed), len(failed)))