import ftplib
import re
from ftplib import FTP

def acc2path(acc):
    """将GenBank Accession编号转换为NCBI FTP路径"""
    root = '/genomes/all/GCA/'
    acc_part = acc.split('_')[1].split('.')[0]  # 提取中间数字部分
    return f"{root}{acc_part[0:3]}/{acc_part[3:6]}/{acc_part[6:9]}"

def extract_version(subdir):
    """从子目录名中提取版本号"""
    match = re.search(r'\.(\d+)(?:_|$)', subdir)
    return int(match.group(1)) if match else 0

def main():
    # 读取Accession列表
    with open('accession.txt', 'r') as f:
        accessions = [line.strip() for line in f if line.strip()]

    ftp = FTP('ftp.ncbi.nlm.nih.gov')
    ftp.login()

    ftp_links = []

    for acc in accessions:
        base_path = acc2path(acc)
        try:
            ftp.cwd(base_path)
        except ftplib.error_perm:
            print(f"错误：路径 {base_path} 不存在（Accession: {acc}）")
            continue

        # 获取子目录列表
        dir_lines = []
        ftp.retrlines('LIST', dir_lines.append)
        subdirs = [line.split()[-1] for line in dir_lines if line.startswith('d')]

        if not subdirs:
            print(f"错误：{base_path} 下没有子目录（Accession: {acc}）")
            continue

        # 提取版本号并选择最大的子目录
        version_subdirs = [(extract_version(subdir), subdir) for subdir in subdirs]
        version_subdirs.sort(reverse=True, key=lambda x: x[0])
        selected_subdir = version_subdirs[0][1]
        full_path = f"{base_path}/{selected_subdir}"

        # 进入选中的子目录
        try:
            ftp.cwd(selected_subdir)
        except ftplib.error_perm:
            print(f"错误：无法进入子目录 {selected_subdir}（Accession: {acc}）")
            continue

        # 获取文件列表
        file_lines = []
        ftp.retrlines('LIST', file_lines.append)
        files = [line.split()[-1] for line in file_lines if not line.startswith('d')]

        # 生成FTP链接
        for filename in files:
            ftp_url = f"ftp://ftp.ncbi.nlm.nih.gov{full_path}/{filename}"
            ftp_links.append(ftp_url)

    ftp.quit()

    # 写入结果文件
    with open('ftp.txt', 'w') as f:
        f.write("\n".join(ftp_links))

    print(f"成功生成 {len(ftp_links)} 个FTP链接到 ftp.txt")

    # 后处理筛选.fna.gz文件
    with open('ftp.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    filtered_urls = [
        url for url in urls
        if url.endswith('.fna.gz') 
        and '_cds_' not in url 
        and '_rna_' not in url
    ]
    
    with open('fna-ftp.txt', 'w') as f_out:
        f_out.write("\n".join(filtered_urls))
    
    print(f"成功提取 {len(filtered_urls)} 个fna.gz链接到 fna-ftp.txt")

if __name__ == '__main__':
    main()
