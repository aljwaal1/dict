from pathlib import Path

p = Path('lib/main.dart')
text = p.read_text(encoding='utf-8')

text = text.replace("const appVersion = '2.2.0';", "const appVersion = '2.2.2';")
text = text.replace("const appVersion = '2.2.1';", "const appVersion = '2.2.2';")

text = text.replace(
"  bool ttsReady = false;\n",
"  bool ttsReady = false;\n  bool freshInstall = false;\n",
1,
)

text = text.replace(
"    prefs = await SharedPreferences.getInstance();\n    sound = prefs.getBool('sound') ?? true;",
"    prefs = await SharedPreferences.getInstance();\n    freshInstall = prefs.getBool('installation_initialized') != true;\n    await prefs.setBool('installation_initialized', true);\n    sound = prefs.getBool('sound') ?? true;",
1,
)

share_anchor = """  Future<void> shareBackup() async {
    final file = await createBackupFile();
    await Share.shareXFiles([XFile(file.path)], subject: 'نسخة احتياطية - قاموسي المدرسي', text: 'نسخة احتياطية كاملة للكلمات والتقدم والملفات الشخصية.');
  }
"""

save_method = share_anchor + """

  Future<bool> savePersistentBackupToDevice() async {
    final payload = {
      'app': 'قاموسي المدرسي',
      'format': 'qamoosi-backup',
      'formatVersion': 2,
      'appVersion': appVersion,
      'createdAt': DateTime.now().toIso8601String(),
      'preferences': _allPrefsSnapshot(),
      'words': words.map((e) => e.toJson()).toList(),
    };
    final bytes = Uint8List.fromList(
      utf8.encode(const JsonEncoder.withIndent('  ').convert(payload)),
    );
    final saved = await FilePicker.platform.saveFile(
      dialogTitle: 'حفظ نسخة احتياطية دائمة',
      fileName: 'qamoosi_backup_latest.json',
      type: FileType.custom,
      allowedExtensions: ['json'],
      bytes: bytes,
    );
    return saved != null;
  }
"""
if 'savePersistentBackupToDevice' not in text:
    if share_anchor not in text:
        raise SystemExit('shareBackup anchor not found')
    text = text.replace(share_anchor, save_method, 1)

bootstrap_old = """    store.init().then((_) { if (mounted) setState(() => ready = true); });
  }
"""
bootstrap_new = """    store.init().then((_) {
      if (!mounted) return;
      setState(() => ready = true);
      if (store.freshInstall) {
        WidgetsBinding.instance.addPostFrameCallback((_) => _offerRecovery());
      }
    });
  }

  Future<void> _offerRecovery() async {
    if (!mounted) return;
    final restore = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('استعادة بياناتك السابقة؟'),
        content: const Text('إذا كنت قد حذفت التطبيق سابقاً ولديك نسخة محفوظة في الجهاز، يمكنك استعادتها الآن. لن يستطيع التطبيق قراءة النسخ الخارجية دون اختيارك للملف.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('ليس الآن')),
          FilledButton.icon(
            onPressed: () => Navigator.pop(dialogContext, true),
            icon: const Icon(Icons.restore_rounded),
            label: const Text('استعادة من الجهاز'),
          ),
        ],
      ),
    );
    if (restore != true || !mounted) return;
    try {
      await store.restoreBackup(replace: true);
      if (mounted) snack(context, 'تمت استعادة بياناتك السابقة بنجاح');
    } catch (e) {
      if (mounted) snack(context, 'تعذر استعادة النسخة: $e');
    }
  }
"""
if '_offerRecovery()' not in text:
    if bootstrap_old not in text:
        raise SystemExit('bootstrap anchor not found')
    text = text.replace(bootstrap_old, bootstrap_new, 1)

settings_anchor = """          SettingsTile(icon: Icons.cloud_upload_outlined, title: 'تصدير نسخة احتياطية كاملة', subtitle: 'الكلمات والتقدم والنقاط والملفات الشخصية', onTap: () async { try { await store.shareBackup(); } catch (e) { if (context.mounted) snack(context, 'تعذر إنشاء النسخة: $e'); } }),
          SettingsTile(icon: Icons.restore_rounded, title: 'استعادة نسخة احتياطية', subtitle: 'يدعم الدمج أو الاستبدال', onTap: () => restoreDialog(context)),
"""
settings_new = """          SettingsTile(
            icon: Icons.save_alt_rounded,
            title: 'حفظ نسخة دائمة على الجهاز',
            subtitle: 'تبقى في تطبيق الملفات حتى بعد حذف التطبيق وإعادة تثبيته',
            onTap: () async {
              try {
                final ok = await store.savePersistentBackupToDevice();
                if (!context.mounted) return;
                if (ok) snack(context, 'تم حفظ النسخة الدائمة. احتفظ بملف qamoosi_backup_latest.json في الجهاز');
              } catch (e) {
                if (context.mounted) snack(context, 'تعذر حفظ النسخة على الجهاز: $e');
              }
            },
          ),
          SettingsTile(icon: Icons.cloud_upload_outlined, title: 'مشاركة نسخة احتياطية', subtitle: 'إرسال النسخة إلى Drive أو واتساب أو أي مكان آمن', onTap: () async { try { await store.shareBackup(); } catch (e) { if (context.mounted) snack(context, 'تعذر إنشاء النسخة: $e'); } }),
          SettingsTile(icon: Icons.restore_rounded, title: 'استعادة نسخة من الجهاز', subtitle: 'بعد إعادة التثبيت اختر ملف qamoosi_backup_latest.json أو أي نسخة سابقة', onTap: () => restoreDialog(context)),
"""
if "title: 'حفظ نسخة دائمة على الجهاز'" not in text:
    if settings_anchor not in text:
        raise SystemExit('settings backup anchor not found')
    text = text.replace(settings_anchor, settings_new, 1)

p.write_text(text, encoding='utf-8')
print('Applied v2.2.2 persistent backup/reinstall recovery patch')
