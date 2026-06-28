# Labs Clipboard v0.6 Direct Send

Bu sürüm eşleşme sonrası gönderememe sorununu hedefler.

Değişiklikler:
- Eşleşen cihazın IP adresi artık `peers.json` içine kaydedilir.
- UDP discovery görünmese bile kayıtlı IP ile gönderim denenir.
- Cihaz kartında IP görünür.
- Cihaz kartına **Test** butonu eklendi.
- Ping mesajı eklendi; iki tarafın gerçekten birbirini eşleşmiş gördüğünü test eder.
- Discovery MAGIC v0.6 yapıldı, eski sürüm cihazları karışmasın.

Test:
1. Eski Pano/Labs uygulamalarını iki bilgisayarda da tamamen kapat.
2. Bu v0.6 paketini iki bilgisayarda da çalıştır.
3. Gerekirse eski eşleşmeleri silip yeniden eşleştir.
4. Cihaz kartındaki **Test** butonuna bas.
5. Test çalışırsa metin/dosya gönderimini dene.

Not:
Eğer Test başarısızsa sorun Windows Güvenlik Duvarı, yanlış IP, farklı Wi-Fi/VLAN veya karşı tarafta uygulamanın kapalı olmasıdır.
